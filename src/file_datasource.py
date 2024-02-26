from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking
from domain.aggregated_data import AggregatedData
import config


class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
        parking_filename: str
    ) -> None:
        self.accelerometer_filename = accelerometer_filename;
        self.gps_filename = gps_filename;
        self.parking_filename = parking_filename;

        self.accelerometer_file = None;
        self.gps_file = None;
        self.parking_file = None;

    def read(self) -> AggregatedData:
        """Метод повертає дані отримані з датчиків"""
        accelerometer_data = self.accelerometer_file.readline().strip().split(',')
        gps_data = self.gps_file.readline().strip().split(',')
        parking_data = self.parking_file.readline().strip().split(',')

        if accelerometer_data and gps_data and parking_data:
          empty_count = int(parking_data[0])
          parking_gps = Gps(*map(float, parking_data[1:]))

          parking = Parking(empty_count, parking_gps)

          return AggregatedData(
              Accelerometer(*map(int, accelerometer_data)),
              Gps(*map(float, gps_data)),
              parking,
              datetime.now(),
              config.USER_ID,
          )

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        self.accelerometer_file = open(self.accelerometer_filename, 'r');
        self.gps_file = open(self.gps_filename, 'r');
        self.parking_file = open(self.parking_filename, 'r');

        next(self.accelerometer_file);
        next(self.gps_file);
        next(self.parking_file);

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        if self.accelerometer_file:
            self.accelerometer_file.close()
        if self.gps_file:
            self.gps_file.close()
        if self.parking_file:
            self.parking_file.close()
