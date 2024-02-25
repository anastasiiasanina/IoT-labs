from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
import config


class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
    ) -> None:
        self.accelerometer_filename = accelerometer_filename;
        self.gps_filename = gps_filename;
        self.accelerometer_file = None;
        self.gps_file = None;

    def read(self) -> AggregatedData:
        """Метод повертає дані отримані з датчиків"""
        accelerometer_data = self.accelerometer_file.readline().strip().split(',')
        gps_data = self.gps_file.readline().strip().split(',')

        if accelerometer_data and gps_data:
          return AggregatedData(
              Accelerometer(*map(int, accelerometer_data)),
              Gps(*map(float, gps_data)),
              datetime.now(),
              config.USER_ID,
          )

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        self.accelerometer_file = open(self.accelerometer_filename, 'r');
        self.gps_file = open(self.gps_filename, 'r');

        next(self.accelerometer_file);
        next(self.gps_file);

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        if self.accelerometer_file:
            self.accelerometer_file.close()
        if self.gps_file:
            self.gps_file.close()
